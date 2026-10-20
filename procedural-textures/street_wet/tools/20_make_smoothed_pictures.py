# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------------------------
# Round 2 of the wet street. It makes SMOOTHED copies of the street's photo pictures (no Blender needed, plain Python with numpy and PIL).
#
# Why: when the road is wet, water fills the finest grain of the stones and only the big shapes (the joints between setts, the dome of each stone) stay. The
# first round let a wet road keep ALL the photo's fine grain in its relief picture (its "normal map": a picture that tells every dot which way it faces). Drawn
# with EEVEE (the fast renderer the film's plates are drawn with) a glossy surface with that grain throws a white speckle at every dot ("grit"), which is
# the first problem the checker found. A smoothed copy keeps the joints and loses the grain, and the layer slides from the sharp picture to the smoothed
# one as wetness rises (the new input "Wet Normal" of the WETNESS layer).
#
# Example: square_cobblestone_normal.jpg is 1024 dots for 2 m, so one dot is 2 mm. Smoothing it with a blur 2 dots wide (4 mm) removes grain 2 to 4 mm
# across and keeps joints that are 1 cm (5 dots) wide, which is what the road needs.
#
# What it reads:  set_copy/textures/<name>_normal.jpg, set_copy/polyhaven_maps/<name>_displacement.jpg
# What it writes: set_copy/polyhaven_maps/<name>_normal_smooth_<sigma>.png and <name>_displacement_smooth_<sigma>.png  (sigma = blur width in dots)
# Run: python3 -I tools/20_make_smoothed_pictures.py NAME SIGMA [NAME SIGMA ...]      e.g.  python3 -I tools/20_make_smoothed_pictures.py square_cobblestone 2
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
TEX = f'{ROOT}/set_copy/textures'
MAPS = f'{ROOT}/set_copy/polyhaven_maps'


def blur(array, sigma):
    """Gaussian blur of a 2-D or 3-D float array, wrapping around the edges (these pictures tile)."""
    if sigma <= 0:
        return array
    radius = int(np.ceil(sigma * 3))
    x = np.arange(-radius, radius + 1)
    kernel = np.exp(-(x ** 2) / (2 * sigma ** 2))
    kernel /= kernel.sum()
    out = array
    for axis in (0, 1):
        padded = np.concatenate([np.take(out, np.arange(-radius, 0), axis=axis, mode='wrap'), out, np.take(out, np.arange(0, radius), axis=axis, mode='wrap')], axis=axis)
        result = np.zeros_like(out)
        for offset, weight in enumerate(kernel):
            index = [slice(None)] * out.ndim
            index[axis] = slice(offset, offset + out.shape[axis])
            result += weight * padded[tuple(index)]
        out = result
    return out


def smooth_normal(path, sigma, out_path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0 * 2 - 1       # -1..1 directions
    b = blur(a, sigma)
    length = np.sqrt((b ** 2).sum(axis=2, keepdims=True))
    b = b / np.maximum(length, 1e-6)
    # keep the flat part exactly as it was: average tilt only
    Image.fromarray(np.clip((b * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)).save(out_path)
    tilt_before = np.sqrt(a[..., 0] ** 2 + a[..., 1] ** 2).mean()
    tilt_after = np.sqrt(b[..., 0] ** 2 + b[..., 1] ** 2).mean()
    return tilt_before, tilt_after


def smooth_grey(path, sigma, out_path):
    a = np.asarray(Image.open(path).convert('L')).astype(np.float64) / 255.0
    b = blur(a, sigma)
    Image.fromarray(np.clip(b * 255 + 0.5, 0, 255).astype(np.uint8)).save(out_path)
    return a.std(), b.std()


if __name__ == '__main__':
    args = sys.argv[1:]
    for name, sigma in zip(args[0::2], args[1::2]):
        sigma = float(sigma)
        tag = f'{sigma:g}'
        normal_path = f'{TEX}/{name}_normal.jpg'
        if os.path.exists(normal_path):
            before, after = smooth_normal(normal_path, sigma, f'{MAPS}/{name}_normal_smooth_{tag}.png')
            print(f'{name} normal: mean tilt {before:.4f} -> {after:.4f} (blur {sigma} dots)')
        height_path = f'{MAPS}/{name}_displacement.jpg'
        if os.path.exists(height_path):
            before, after = smooth_grey(height_path, sigma, f'{MAPS}/{name}_displacement_smooth_{tag}.png')
            print(f'{name} height: spread {before:.4f} -> {after:.4f}')
