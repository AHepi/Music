# What this does (plain words): scores ANY colour picture (a numpy array) as if it had been baked: it makes the height and the normal from the colour with the
# same rule the generator uses (height = a straight mix of red, green, blue with cut-offs, blurred 0.5 dots; normal = slope of the 8-bit height, strength 10),
# writes colour/height/normal into a folder and runs the project's dot-for-dot comparison. Used for quick "what could a description of this kind ever reach"
# experiments without a Blender bake. Plain Python (python3 -I).
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'lib'))
import pixel_compare as pc

MIX = np.array([267.15, 91.48, 210.5]) / 255.0


def derive(colour_bgr, strength=10, kernel='central', blur=0.5):
    rgb = colour_bgr[..., ::-1].astype(np.float64)
    blurred = cv2.GaussianBlur(np.pad(rgb, ((8, 8), (8, 8), (0, 0)), mode='wrap'), (0, 0), blur)[8:-8, 8:-8] if blur > 0 else rgb
    height = np.clip(blurred @ MIX - 17.7, 0, 255)
    h = np.round(height)
    if kernel == 'sobel':
        at = lambda di, dj: np.roll(np.roll(h, -di, 0), -dj, 1)
        hx = ((at(-1, 1) + 2 * at(0, 1) + at(1, 1)) - (at(-1, -1) + 2 * at(0, -1) + at(1, -1))) / 8.0
        hy = ((at(1, -1) + 2 * at(1, 0) + at(1, 1)) - (at(-1, -1) + 2 * at(-1, 0) + at(-1, 1))) / 8.0
    else:
        hx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2.0
        hy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    normal = np.stack([nx / length, ny / length, nz / length], axis=-1)
    return height, normal


def score_picture(colour_bgr, folder, strength=10, kernel='central'):
    os.makedirs(folder, exist_ok=True)
    height, normal = derive(colour_bgr, strength, kernel)
    cv2.imwrite(os.path.join(folder, 'colour.png'), colour_bgr)
    cv2.imwrite(os.path.join(folder, 'height.png'), (height / 255.0 * 65535).round().astype(np.uint16))
    cv2.imwrite(os.path.join(folder, 'normal.png'), ((normal * 0.5 + 0.5) * 255).round().astype(np.uint8)[..., ::-1])
    r = pc.pixel_report('gravel', folder)
    keep = ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached']
    return {k: (round(r[k], 3) if isinstance(r[k], float) else r[k]) for k in keep}


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    import trace_tools as tt
    bgr = tt.load_reference_colour()
    centres = tt.make_palette(bgr, 24)
    labels = tt.assign_labels(bgr, centres)
    palette_bgr = tt.palette_to_bgr(centres)
    snapped = palette_bgr[labels]
    tmp = os.path.join(HERE, '..', 'scores', 'tmp_numpy_bake')
    print('snapped to 24 colours, no dot dropped (ceiling of a flat palette picture):', score_picture(snapped, os.path.join(tmp, 'snap24')), flush=True)
    for kernel, strength in (('central', 10), ('sobel', 12)):
        print('  derived with', kernel, strength, score_picture(snapped, os.path.join(tmp, 'snap24'), strength, kernel), flush=True)
    filtered = tt.mode_filter(labels, 24, 1)
    print('snapped + 3x3 mode filter:', score_picture(palette_bgr[filtered], os.path.join(tmp, 'snap24f')), flush=True)
