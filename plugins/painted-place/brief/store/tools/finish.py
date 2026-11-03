"""
What this file does: an optional finish for a drawn picture. It takes the raw render and writes the finished picture:
glow round the bright lamps, a film curve that keeps orange orange instead of burning it white, blue-black shadows that
are never pure black, a little warmth in the lights, a painter's softening of small detail, a vignette and a fine grain.
Every step is a dial; set a dial to 0 to leave that step out. Using it is optional: a picture drawn and graded in
Blender itself is just as good if it holds the look.

From the command line:

    python3 finish.py raw.exr finished.png                 (best: a raw 32-bit EXR, light as it was drawn)
    python3 finish.py raw.png finished.png --soften 0.6    (a PNG already through Blender's view transform also works)
    python3 finish.py --help

From your own script:

    import finish
    finish.finish('raw.exr', 'finished.png', exposure=1.0, bloom=1.0, shadows_blue=1.0)

To draw a raw EXR in Blender: scene.render.image_settings.file_format = 'OPEN_EXR'; color_depth = '32'. An EXR holds
the light as drawn (linear), so the film curve here does the work Blender's view transform would; a PNG has already
been through the view transform, so the curve is skipped for it.

Dials, with their defaults (0 leaves the step out):
    exposure      1.0    brightness before the curve (EXR only)
    bloom         1.0    glow round bright lamps and windows
    veil          0.0    a warm band of lit air along the horizon (dusty or misty air); veil_height says where (0.575 = a little below the middle)
    shadows_blue  1.0    shadows and darks pulled towards blue-black
    floor         1.0    blacks lifted to a blue-black floor, never pure black
    warm_lights   1.0    a little extra warmth in the lightest parts
    soften        0.5    a painter's softening: small detail merged, edges kept
    vignette      1.0    corners darkened
    grain         1.0    a fine film grain
"""

import argparse
import os
import sys

import numpy as np

TOOL = {
    'name': 'finish',
    'what': 'optional: turns a raw render into the finished picture (lamp glow, a curve that keeps orange orange, blue-black darks, softening, vignette, grain)',
    'call': "finish.finish('raw.exr', 'finished.png', bloom=1.0, soften=0.5)",
    'options': {
        'exposure': 'brightness before the curve, EXR only (1.0)',
        'bloom': 'glow round bright lamps and windows (1.0)',
        'veil': 'a warm band of lit air along the horizon (0: none); veil_height where it lies (0.575)',
        'shadows_blue': 'darks pulled towards blue-black (1.0)',
        'floor': 'blacks lifted to a blue-black floor (1.0)',
        'warm_lights': 'extra warmth in the lightest parts (1.0)',
        'soften': "a painter's softening of small detail, edges kept (0.5)",
        'vignette': 'corners darkened (1.0)',
        'grain': 'fine film grain (1.0)',
    },
    'materials': [],
    'source': "the desert mine builder's finish (log 46) with the military base builder's softening (log 50)",
    'trap': 'give it the raw EXR if you can: a PNG has already been through a curve, and a second curve flattens it',
}


def read_picture(path):
    """The picture as floats, and whether it is linear light (an EXR) or already for the screen (a PNG or JPEG)."""
    if path.lower().endswith('.exr'):
        import bpy
        image = bpy.data.images.load(os.path.abspath(path))
        width, height = image.size
        pixels = np.empty(width * height * 4, dtype=np.float32)
        image.pixels.foreach_get(pixels)
        bpy.data.images.remove(image)
        return pixels.reshape(height, width, 4)[::-1, :, :3].copy(), True
    from PIL import Image
    return np.asarray(Image.open(path).convert('RGB'), dtype=np.float32) / 255.0, False


def _luminance(picture):
    return picture[..., 0] * 0.2126 + picture[..., 1] * 0.7152 + picture[..., 2] * 0.0722


def _blur(picture, sigma):
    from scipy import ndimage
    if picture.ndim == 2:
        return ndimage.gaussian_filter(picture, sigma)
    return np.stack([ndimage.gaussian_filter(picture[..., c], sigma) for c in range(picture.shape[2])], axis=-1)


def finish(source, target, exposure=1.0, bloom=1.0, veil=0.0, veil_height=0.575, shadows_blue=1.0, floor=1.0,
           warm_lights=1.0, soften=0.5, vignette=1.0, grain=1.0, seed=3):
    picture, linear = read_picture(source)
    height, width, _ = picture.shape
    size = height / 960.0
    if linear:
        light = np.maximum(picture, 0.0) * exposure
        if veil > 0:      # lit air lying along the horizon
            rows, columns = np.mgrid[0:height, 0:width]
            band = np.exp(-((rows - veil_height * height) / (0.075 * height)) ** 2) * (1.0 - 0.55 * columns / width)
            light = light + (band * 0.17 * veil)[..., None] * np.array([0.34, 0.16, 0.05])
        if bloom > 0:     # glow round bright things, in linear light so it behaves like light
            level = _luminance(light)
            bright = np.clip(level - 0.9, 0, 8)[..., None] * light / np.maximum(level, 1e-4)[..., None]
            light = light + bloom * (0.3 * _blur(bright, 6 * size) + 0.32 * _blur(bright, 22 * size) * np.array([1.0, 0.72, 0.42]))
        a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14          # a film curve per channel: orange stays orange
        screen = np.clip((light * (a * light + b)) / (light * (c * light + d) + e), 0, 1)
        screen = np.where(screen <= 0.0031308, screen * 12.92, 1.055 * np.power(np.maximum(screen, 1e-6), 1 / 2.4) - 0.055)
    else:
        screen = picture.copy()
        if bloom > 0:
            level = screen.max(axis=2)
            bright = np.clip((level - 0.6) / 0.4, 0, 1)[..., None] * screen
            screen = screen + bloom * (0.30 * _blur(bright, 4.0 * size * 1.8) + 0.24 * _blur(bright, 14.0 * size * 1.8))
    level = _luminance(screen)[..., None]
    if shadows_blue > 0:   # blue-black darks, a cool cast in the shadows; anything lit warm keeps its warmth
        teal = np.array([0.03, 0.09, 0.13])
        warmth = np.clip((screen[..., 0:1] - screen[..., 2:3]) / np.maximum(screen[..., 0:1], 1e-3) * 2.5, 0, 1)
        weight = ((1 - np.clip(level / 0.2, 0, 1)) ** 2) * 0.32 * shadows_blue * (1 - warmth)
        shade = np.clip(1 - level * 6.0, 0, 1) ** 2 * (1 - warmth)
        screen = screen * (1 - weight) + (level * 0.9 + 0.01) * (teal / teal.mean() * 0.9) * weight + shade * np.array([-0.003, 0.006, 0.014]) * shadows_blue
    if warm_lights > 0:
        screen = screen * (1 + 0.06 * warm_lights * np.clip(level - 0.5, 0, 1) * np.array([1.0, 0.2, -0.6]))
    if floor > 0:          # blacks are never pure
        bottom = np.array([0.012, 0.030, 0.044]) * floor
        screen = bottom + screen * (1 - bottom)
    screen = np.clip(screen, 0, 1)
    if soften > 0:         # a painter's softening: small detail merged, edges kept
        import cv2
        k = width / 540.0
        eight = (screen * 255 + 0.5).astype(np.uint8)
        smooth = cv2.bilateralFilter(eight, 0, 15, 2.5 * k)
        smooth = cv2.bilateralFilter(smooth, 0, 11, 1.5 * k).astype(np.float32) / 255.0
        screen = screen * (1 - soften) + smooth * soften
        sharp = _blur(screen, 1.2 * k)
        screen = np.clip(screen + 0.35 * soften * (screen - sharp), 0, 1)
    if vignette > 0:
        rows, columns = np.mgrid[0:height, 0:width]
        radius = np.sqrt(((columns - width / 2) / (width / 2)) ** 2 + ((rows - height * 0.5) / (height / 2)) ** 2)
        screen = screen * (1 - 0.32 * vignette * np.clip(radius - 0.4, 0, 1.2) ** 1.5)[..., None]
    if grain > 0:
        noise = _blur(np.random.default_rng(seed).normal(0, 1, (height, width)), 0.7 * size)
        screen = screen + (noise * 0.011 * grain)[..., None]
    screen = np.clip(screen, 0, 1)
    from PIL import Image
    Image.fromarray((screen * 255 + 0.5).astype(np.uint8)).save(target)
    return target


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description='Turn a raw render into the finished picture (see the note at the top of finish.py).')
    parser.add_argument('source', help='the raw render: a 32-bit EXR (best) or a PNG')
    parser.add_argument('target', help='where to write the finished picture (PNG or JPEG)')
    for name, default in (('exposure', 1.0), ('bloom', 1.0), ('veil', 0.0), ('veil-height', 0.575), ('shadows-blue', 1.0),
                          ('floor', 1.0), ('warm-lights', 1.0), ('soften', 0.5), ('vignette', 1.0), ('grain', 1.0)):
        parser.add_argument('--' + name, type=float, default=default)
    args = parser.parse_args(argv)
    print(finish(args.source, args.target, exposure=args.exposure, bloom=args.bloom, veil=args.veil, veil_height=args.veil_height,
                 shadows_blue=args.shadows_blue, floor=args.floor, warm_lights=args.warm_lights, soften=args.soften,
                 vignette=args.vignette, grain=args.grain))


if __name__ == '__main__':
    main()
