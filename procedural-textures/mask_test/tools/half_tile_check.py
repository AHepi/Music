# What this does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------
# The "half-tile shift test": a texture that repeats without a seam must look exactly the same when you slide the pattern by any amount
# and slide the picture back. The recipe has a parameter `shift` that slides the pattern by a part of the tile. So:
#     picture made with shift (0.5, 0.5)  must equal  the unshifted picture with its rows and columns rolled by half the picture.
# If a stamp stopped at the tile edge instead of wrapping, the two pictures would differ along the old tile edge (which sits in the middle
# of the shifted picture). This script bakes nothing: it reads the pictures that bake_jobs.py made at 512 dots (work/half/...) and measures
# how much the shifted picture differs from the rolled one, and how many stamp dots lie at the tile edge (so the test is not empty).
# Run:  python3 -I half_tile_check.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
MASK = os.path.abspath(os.path.join(HERE, '..'))
HALF = os.path.join(MASK, 'work', 'half')
SIZE = 512


def read(path, as_mask=False):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if as_mask:
        image = image[..., 0] if image.ndim == 3 else image
        return image.astype(np.float64) / 65535.0
    return image.astype(np.float64) / 255.0


def predicted(base, shift_u, shift_v):
    """What the shifted picture must look like: u grows to the right, v grows UP the picture."""
    columns = int(round(shift_u * SIZE))
    rows = int(round(shift_v * SIZE))
    return np.roll(np.roll(base, -columns, axis=1), rows, axis=0)


def edge_pieces(mask, threshold=0.5, band=3):
    """Number of separate mask pieces that touch the picture edge, and mask dots within 40 dots of the edge."""
    binary = (mask > threshold).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    touching = set()
    for edge in (labels[:band].ravel(), labels[-band:].ravel(), labels[:, :band].ravel(), labels[:, -band:].ravel()):
        touching |= set(int(v) for v in edge if v > 0)
    near = np.zeros_like(binary, bool)
    near[:40], near[-40:], near[:, :40], near[:, -40:] = True, True, True, True
    return len(touching), int((binary.astype(bool) & near).sum())


def main():
    results = {}
    tests = [
        # name, base folder, shifted folder, shift, is a mask (height channel holds the exact number) or a colour picture
        ('moss stamp mask', 'moss_mask_0', 'moss_mask_half', (0.5, 0.5), True),
        ('chip stamp mask', 'chip_mask_0', 'chip_mask_half', (0.5, 0.5), True),
        ('finished colour, moss and chip stamps', 'both_0', 'both_half', (0.5, 0.5), False),
        ('finished colour, moss and chip stamps, other slide', 'both_0', 'both_slide', (0.25, 0.375), False),
        ('finished colour, node-made (control)', 'nodes_0', 'nodes_half', (0.5, 0.5), False),
    ]
    for label, base_name, shifted_name, shift, is_mask in tests:
        file_name = 'height.png' if is_mask else 'colour.png'
        base = read(os.path.join(HALF, base_name, file_name), is_mask)
        shifted = read(os.path.join(HALF, shifted_name, file_name), is_mask)
        expected = predicted(base, *shift)
        difference = np.abs(shifted - expected)
        if difference.ndim == 3:
            difference = difference.max(axis=2)
        threshold = 0.02 if is_mask else 8.0 / 255.0
        row = {'shift': list(shift), 'largest_difference': round(float(difference.max()), 4), 'mean_difference': round(float(difference.mean()), 6),
               'share_of_dots_differing_more_than_limit': round(float((difference > threshold).mean()), 6), 'limit': round(threshold, 4)}
        # where the old tile edges lie in the shifted picture: a column and a row. If a stamp did not wrap, the differences would pile up there.
        edge_column = int(round(((1.0 - shift[0]) % 1.0) * SIZE)) % SIZE
        edge_row = int(round((shift[1] % 1.0) * SIZE)) % SIZE
        near = np.zeros(difference.shape, bool)
        for offset in range(-3, 4):
            near[:, (edge_column + offset) % SIZE] = True
            near[(edge_row + offset) % SIZE, :] = True
        over = difference > threshold
        # The renderer takes only 4 samples per dot with a random jiggle, so the dots on sharp edges differ a little between two renderings of the same
        # picture. A real seam would show as a missing or cut-off piece, which survives a blur. So the same numbers are also measured after a gentle blur.
        blur = lambda a: cv2.GaussianBlur(a.astype(np.float32), (0, 0), 1.5)
        blurred = np.abs(blur(shifted) - blur(expected))
        if blurred.ndim == 3:
            blurred = blurred.max(axis=2)
        blur_limit = 0.06 if is_mask else 0.03
        row['after_blur_largest_difference'] = round(float(blurred.max()), 4)
        row['after_blur_dots_over_limit'] = int((blurred > blur_limit).sum())
        row['after_blur_limit'] = blur_limit
        row['after_blur_dots_over_limit_in_the_band_along_the_old_tile_edge'] = int(((blurred > blur_limit) & near).sum())
        row['share_over_limit_in_the_7_dot_band_along_the_old_tile_edge'] = round(float(over[near].mean()), 5)
        row['share_over_limit_everywhere_else'] = round(float(over[~near].mean()), 5)
        row['old_tile_edge_column_and_row_in_shifted_picture'] = [edge_column, edge_row]
        if is_mask:
            pieces, near = edge_pieces(base)
            row['mask_pieces_touching_tile_edge'] = pieces
            row['mask_dots_within_40_of_tile_edge'] = near
            row['mask_share_over_half'] = round(float((base > 0.5).mean()), 4)
        results[label] = row
    json.dump(results, open(os.path.join(MASK, 'work', 'half_tile_results.json'), 'w'), indent=1)
    for label, row in results.items():
        print(label, json.dumps(row))


if __name__ == '__main__':
    main()
