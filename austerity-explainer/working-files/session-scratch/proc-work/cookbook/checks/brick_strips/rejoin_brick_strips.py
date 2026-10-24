# What this does (plain words): re-joins the brick builder's "what does this setting do?" squares (recipes/brick/guide_pictures/sweeps/<name>/tile_XX.png,
# read only, never changed) into new strips for the brick guide, fixing three things the checker found in the old strips:
#   1. the squares touched with no gap, so the join between two squares looked like a crack in a brick: now every square has a white gap;
#   2. the label "(reference)" really meant "the sampler's default value": now it says "(default)";
#   3. the small crops were stretched to squares: now they are enlarged 2 x with hard dot edges and padded with white, so nothing is stretched.
# It also makes ONE new strip that the builder never made: the normal map "strength" (the number that turns the height's slope into the normal map),
# from the height picture of sampled tile 11 (recipes/brick/variations/tile_11/height.png), using the same slope formula as generator/derive_maps.py.
# The joining itself is done by the shared lib/make_strip.py; each strip is then stored with at most 256 colours to keep it small.
# Output: proc-work/cookbook/pictures/brick-strip-*.png
# Run with the system python:  python3 -I -B rejoin_brick_strips.py
import json
import os
import shutil
import subprocess
import sys

import cv2
import numpy as np

PROC = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work'
SWEEPS = os.path.join(PROC, 'recipes', 'brick', 'guide_pictures', 'sweeps')
WORK = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strip_tiles')
OUT = os.path.join(PROC, 'cookbook', 'pictures')
MAKE_STRIP = os.path.join(PROC, 'lib', 'make_strip.py')
GAP = 10          # white gap (in dots of the enlarged square) on the right of every square

# name -> (new labels, title, zoom) ; zoom = (x0, y0, x1, y1) part of the square to keep before enlarging (None = all)
STRIPS = {
    'grain_amount': (['grain 0', '0.05', '0.10', '0.15', '0.25'], 'Brick: grain amount (White Noise, one number per dot)', None),
    'corner_radius': (['radius 0', '5', '9 (default)', '16', '26'], 'Brick: corner radius (dots)', None),
    'outline_ring_width': (['no ring', 'x1', 'x2 (default)', 'x4', 'x7'], 'Brick: dark outline ring width', None),
    'edge_wobble': (['wobble 0', '0.6', '1.3 (default)', '2.5', '4.5'], 'Brick: wobble of the patch edges (dots)', None),
    'soot_smudges': (['soot 0', '6', '12', '24', '48'], 'Brick: number of soot clouds per tile (default 14)', None),
    'big_cell_area': (['area 5000', '2500', '1100 (see guide)', '500', '220'], 'Brick: area of the biggest paint patches (dots)', None),
    'number_of_cell_sizes': (['1 size', '2 sizes', '3 sizes', '4 sizes (default)'], 'Brick: how many patch sizes are layered', None),
    'height_blur': (['blur 0', '0.7 (default, fitted)', '1.5', '3', '6'], 'Brick: blur before the height is made (normal map shown)', None),
    'tone_jitter': (['jitter 0', '0.08 (about default)', '0.2', '0.4', '0.8'], 'Brick: tone jitter of the big patches (middle of the tile, 2x)', (96, 96, 288, 288)),
}


def square_with_gap(image, zoom):
    if zoom:
        x0, y0, x1, y1 = zoom
        image = image[y0:y1, x0:x1]
    image = cv2.resize(image, (image.shape[1] * 2, image.shape[0] * 2), interpolation=cv2.INTER_NEAREST)   # hard dot edges
    h, w = image.shape[:2]
    side = max(h, w)
    canvas = np.full((side, side + GAP, 3), 255, np.uint8)
    top, left = (side - h) // 2, (side - w) // 2
    canvas[top:top + h, left:left + w] = image
    out = np.full((side + GAP, side + GAP, 3), 255, np.uint8)       # make_strip wants squares: add the same gap at the bottom
    out[:side, :] = canvas
    return out


def join(folder, labels, title, out_name, columns=None):
    info = {'files': sorted(f for f in os.listdir(folder) if f.startswith('tile_')), 'labels': labels}
    with open(os.path.join(folder, 'sweep.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    command = [sys.executable, '-I', MAKE_STRIP, folder, os.path.join(OUT, out_name), '--cell', '256', '--title', title]
    if columns:
        command += ['--columns', str(columns)]
    subprocess.run(command, check=True, capture_output=True)


def normal_from_height(height01, strength):
    """The same slope formula as recipes/brick/generator/derive_maps.normal_from_height (copied, so nothing in recipes/ is imported or touched)."""
    def shift(a, dy, dx):
        return np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    h = height01
    gx = (2 * shift(h, 0, -1) - 2 * shift(h, 0, 1) + shift(h, -1, -1) + shift(h, 1, -1) - shift(h, -1, 1) - shift(h, 1, 1)) / 8.0
    gy_down = (2 * shift(h, -1, 0) - 2 * shift(h, 1, 0) + shift(h, -1, -1) + shift(h, -1, 1) - shift(h, 1, -1) - shift(h, 1, 1)) / 8.0
    nx, ny, nz = -strength * gx, strength * gy_down, np.ones_like(h)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5


def main():
    os.makedirs(OUT, exist_ok=True)
    if os.path.isdir(WORK):
        shutil.rmtree(WORK)
    for name, (labels, title, zoom) in STRIPS.items():
        folder = os.path.join(WORK, name)
        os.makedirs(folder)
        for file_name in sorted(f for f in os.listdir(os.path.join(SWEEPS, name)) if f.startswith('tile_')):
            image = cv2.imread(os.path.join(SWEEPS, name, file_name))
            cv2.imwrite(os.path.join(folder, file_name), square_with_gap(image, zoom))
        join(folder, labels, title, f'brick-strip-{name.replace("_", "-")}.png')
    # the new strip: normal strength, on a 120 x 120 dot piece (shown 2 x) of sampled tile 11's height (full resolution, no blur scaling)
    height = cv2.imread(os.path.join(PROC, 'recipes', 'brick', 'variations', 'tile_11', 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
    if height.ndim == 3:
        height = height[..., 0]
    height /= 65535.0 if height.max() > 255 else 255.0
    folder = os.path.join(WORK, 'normal_strength')
    os.makedirs(folder)
    strengths = [0, 2, 6, 12, 24]
    for index, strength in enumerate(strengths):
        normal = normal_from_height(height, strength)                         # whole tile, so the slope wraps round like the generator's
        piece = (normal[300:420, 300:420] * 255.0 + 0.5).astype(np.uint8)[..., ::-1]   # RGB -> BGR for cv2
        cv2.imwrite(os.path.join(folder, f'tile_{index:02d}.png'), square_with_gap(piece, None))
    join(folder, ['strength 0', '2', '6 (default, fitted)', '12', '24'], 'Brick: normal map strength (slope of the height)', 'brick-strip-normal-strength.png')
    shutil.rmtree(WORK)
    # keep the files small (the disk is tight): store each strip with at most 256 colours (no visible change at this size)
    from PIL import Image
    for f in sorted(os.listdir(OUT)):
        if f.startswith('brick-strip-'):
            path = os.path.join(OUT, f)
            Image.open(path).convert('RGB').quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(path, optimize=True)
            print(f, os.path.getsize(path) // 1024, 'KB')


if __name__ == '__main__':
    main()
