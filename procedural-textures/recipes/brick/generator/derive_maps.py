# What this does (plain words): turns a COLOUR picture into the HEIGHT picture and the NORMAL picture with the same simple rule that was
# found in the reference ("derivation" fitted in analysis/derivation_ceiling.py): grey brightness -> a very light blur -> a tone curve ->
# height; slope of the height -> normal map (green points UP the picture, OpenGL style). The rule's numbers (curve points, blur width,
# strength) come from the description file, so another surface or another tile just supplies other numbers. numpy only (it runs inside Blender
# and outside it). Pictures wrap round at the edges, so a seamless colour stays seamless in height and normal.
import numpy as np


def grey_of(colour_srgb, weights=(0.299, 0.587, 0.114)):
    """colour_srgb: array (h, w, 3) with values 0..255 (screen values, not linear). Returns grey 0..255."""
    return colour_srgb[..., 0] * weights[0] + colour_srgb[..., 1] * weights[1] + colour_srgb[..., 2] * weights[2]


def gaussian_blur_wrap(picture, sigma):
    """Separable Gaussian blur that wraps round the edges (so tiles stay seamless)."""
    if sigma <= 0:
        return picture
    radius = max(1, int(np.ceil(sigma * 3)))
    taps = np.exp(-0.5 * (np.arange(-radius, radius + 1) / sigma) ** 2)
    taps /= taps.sum()
    out = np.zeros_like(picture, dtype=np.float64)
    for shift, weight in zip(range(-radius, radius + 1), taps):
        out += weight * np.roll(picture, shift, axis=1)
    result = np.zeros_like(out)
    for shift, weight in zip(range(-radius, radius + 1), taps):
        result += weight * np.roll(out, shift, axis=0)
    return result


def height_from_colour(colour_srgb, maps):
    """Height 0..1 from colour. maps = {'blur_sigma': 0.7, 'curve_x': [...grey values], 'curve_y': [...0..255 levels]}"""
    grey = gaussian_blur_wrap(grey_of(colour_srgb), maps['blur_sigma'])
    height_levels = np.interp(grey, maps['curve_x'], maps['curve_y'])
    return np.clip(height_levels / 255.0, 0.0, 1.0)


def normal_from_height(height01, strength):
    """OpenGL normal map (x right, y UP the picture, z out) as an array 0..1 (ready to save). Sobel slope, as the reference was made."""
    def shift(a, dy, dx):
        return np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    h = height01
    gx = (2 * shift(h, 0, -1) - 2 * shift(h, 0, 1) + shift(h, -1, -1) + shift(h, 1, -1) - shift(h, -1, 1) - shift(h, 1, 1)) / 8.0
    gy_down = (2 * shift(h, -1, 0) - 2 * shift(h, 1, 0) + shift(h, -1, -1) + shift(h, -1, 1) - shift(h, 1, -1) - shift(h, 1, 1)) / 8.0
    # np.roll(a, -1) brings the NEXT sample to this place, so each gradient above is (next - previous)
    nx, ny, nz = -strength * gx, strength * gy_down, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5
