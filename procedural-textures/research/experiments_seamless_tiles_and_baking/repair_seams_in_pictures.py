# What this does: tries three ways of repairing a picture that does NOT tile, using only the picture (no recipe), and measures how well
# each one works. Use it to understand the limits of "fix it afterwards" - the better route is always to make the pattern tile in the first place.
#   1. offset_blend   the classic "make seamless" of photo editors: shift the picture by half a tile, then blend the original over the
#                     shifted copy with a mask that is 1 in the middle and 0 at the edges (so the edges come from the shifted copy)
#   2. periodic_plus_smooth  (Moisan 2011) subtract one very smooth, slowly changing picture so that the left edge exactly matches the
#                     right edge and the top exactly matches the bottom; fine detail is untouched
#   3. mirror_2x2     lay the picture and its mirror images in a 2 x 2 block and shrink to the original size (always seamless, always symmetric)
# Run (plain Python):  python3 -I repair_seams_in_pictures.py INPUT.png OUT_FOLDER
# It writes one picture per method plus a labelled strip, and prints the seam ratio, spread and mirror tell of each.
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'lib'))
import texture_compare as tc  # noqa: E402


def load_grey(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image.ndim == 3:
        image = image[..., :3].mean(axis=-1)
    image = image.astype(np.float64)
    return image / (65535.0 if image.max() > 255 else 255.0)


def offset_blend(image):
    rows, columns = image.shape
    shifted = np.roll(image, (rows // 2, columns // 2), axis=(0, 1))
    u = np.linspace(0, 1, columns)
    v = np.linspace(0, 1, rows)
    tri_u = 1.0 - np.abs(2.0 * u - 1.0)
    tri_v = 1.0 - np.abs(2.0 * v - 1.0)
    mask = np.clip(np.minimum.outer(tri_v, tri_u) * 2.0, 0, 1)
    mask = mask * mask * (3 - 2 * mask)
    return mask * image + (1.0 - mask) * shifted


def periodic_plus_smooth(image):
    """Moisan's periodic-plus-smooth decomposition: returns the periodic component (image minus a smooth correction)."""
    rows, columns = image.shape
    boundary = np.zeros_like(image)
    boundary[:, 0] += image[:, -1] - image[:, 0]
    boundary[:, -1] += image[:, 0] - image[:, -1]
    boundary[0, :] += image[-1, :] - image[0, :]
    boundary[-1, :] += image[0, :] - image[-1, :]
    spectrum = np.fft.fft2(boundary)
    q = np.arange(columns)
    r = np.arange(rows)
    denominator = 2.0 * (2.0 - np.cos(2.0 * np.pi * q / columns)[None, :] - np.cos(2.0 * np.pi * r / rows)[:, None])
    denominator[0, 0] = 1.0
    smooth = -np.real(np.fft.ifft2(spectrum / denominator))   # the true denominator is 2cos+2cos-4 (negative), so the minus sign
    smooth -= smooth.mean()
    return image - smooth


def mirror_2x2(image):
    top = np.hstack([image, image[:, ::-1]])
    block = np.vstack([top, top[::-1]])
    return cv2.resize(block, image.shape[::-1], interpolation=cv2.INTER_AREA)


def report(name, image):
    flipped = image[:, ::-1]
    return {'method': name, 'seam_ratio': round(tc.seam_ratio(image), 2), 'spread': round(float(image.std()), 3),
            'mirror_tell': round(float(np.corrcoef(image.ravel(), flipped.ravel())[0, 1]), 2)}


def main():
    path, out_folder = sys.argv[1], sys.argv[2]
    os.makedirs(out_folder, exist_ok=True)
    stem = os.path.splitext(os.path.basename(path))[0]
    image = load_grey(path)
    results = [report('original', image)]
    pictures = [('original', image)]
    for name, function in (('offset_blend', offset_blend), ('periodic_plus_smooth', periodic_plus_smooth), ('mirror_2x2', mirror_2x2)):
        repaired = np.clip(function(image), 0, 1)
        results.append(report(name, repaired))
        pictures.append((name, repaired))
        cv2.imwrite(os.path.join(out_folder, f'{stem}__{name}.png'), (repaired * 65535).astype(np.uint16))
    cell = 256
    columns = []
    for name, picture in pictures:
        # show the tile moved by half so the old seam sits in the middle as a cross
        half = np.roll(picture, (picture.shape[0] // 2, picture.shape[1] // 2), axis=(0, 1))
        small = cv2.resize((np.clip(half, 0, 1) * 255).astype(np.uint8), (cell, cell), interpolation=cv2.INTER_AREA)
        small = cv2.cvtColor(small, cv2.COLOR_GRAY2BGR)
        banner = np.full((26, cell, 3), 245, np.uint8)
        cv2.putText(banner, name, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (20, 20, 20), 1, cv2.LINE_AA)
        columns.append(np.vstack([banner, small]))
    cv2.imwrite(os.path.join(out_folder, f'{stem}__strip.png'), np.hstack(columns))
    for r in results:
        print(f"{stem:30s} {r['method']:22s} seam_ratio {r['seam_ratio']:7} spread {r['spread']:6} mirror_tell {r['mirror_tell']}")


main()
