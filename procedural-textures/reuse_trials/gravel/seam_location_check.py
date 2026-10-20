# What this does (plain words): a closer look at the half-tile test. When the plain picture is slid by half a tile, a real seam (a place where the
# pattern does not continue across the tile edge) would make the dots that DIFFER from the rolled plain picture crowd along the old tile edge.
# For each picture of the test this counts the share of differing dots (more than 40 of 255) in a band of 4 dots on each side of the old tile edge
# (the lines that lie in the middle of the slid picture) and compares it with the share in all the other dots. Equal shares = the differences are
# scattered over fine one-dot edges (rounding noise on thresholded patterns), not a seam. Writes checks/seam_location.json.
# Use: python3 -I seam_location_check.py
import json
import os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(HERE, 'checks', 'half_tile')


def load(path):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED).astype(np.float64)
    image /= 65535.0 if image.max() > 255 else 255.0
    return image if image.ndim == 3 else image[..., None]


results = {}
for tiles in (1, 2):
    for view, kind in (('finished', 'colour'), ('pieces', 'colour'), ('edge_distance', 'height'), ('soil_mask', 'height'), ('facets_mask', 'height')):
        plain = load(os.path.join(folder, f't{tiles}_plain_{view}_{kind}.png'))
        shifted = load(os.path.join(folder, f't{tiles}_shifted_{view}_{kind}.png'))
        size = plain.shape[0]
        # with 2 tiles across the base tile edge is every size/2 dots: the plain picture's own edge is at 0, and the slid picture's old edge is in the middle
        differs = (np.abs(np.roll(plain, (size // 2, size // 2), axis=(0, 1)) - shifted).max(axis=2) * 255.0) > 40
        band = np.zeros(differs.shape, bool)
        # the old tile edges of the PLAIN picture are at 0 (wrapping) and, for two tiles across, also at size / 2; after rolling by size / 2 they are at size / 2 (and 0)
        edges = [size // 2] if tiles == 1 else [0, size // 2]
        for edge in edges:
            for offset in range(-4, 4):
                band[(edge + offset) % size, :] = True
                band[:, (edge + offset) % size] = True
        results[f'{tiles} tile(s) across, {view}'] = {'share differing in the 4-dot bands on the old tile edges %': round(100 * float(differs[band].mean()), 3),
                                                      'share differing everywhere else %': round(100 * float(differs[~band].mean()), 3)}
with open(os.path.join(HERE, 'checks', 'seam_location.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
for name, row in results.items():
    print(f'{name:40s}', row)
